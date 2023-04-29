# coding: utf-8

import audioop
import copy
import io
import json
import os
import sys
import typing
import wave

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping, Optional, Sequence, Union

import numpy as np
import onnxruntime
from espeak_phonemizer  import Phonemizer


DEFAULT_RATE = 50
DEFAULT_VOLUME = 100

_BOS = "^"
_EOS = "$"
_PAD = "_"


class VoiceNotFoundError(LookupError) :
    pass


@dataclass
class PiperVoice:
    key: str
    name: str
    language: str
    description: str
    location: str
    properties: typing.Optional[typing.Mapping[str, int]] = field(default_factory=dict)

    def __post_init__(self):
        try:
            self.model_path = next(self.location.glob("*.onnx"))
            self.config_path = next(self.location.glob("*.onnx.json"))
        except StopIteration:
            raise RuntimeError(f"Could not load voice from `{os.fspath(self.location)}`")
        self.config = PiperConfig.load_from_json_file(self.config_path)
        self.__piper_model = None
        self.speakers = tuple(self.config.speaker_id_map.keys())

    @property
    def model(self):
        if self.__piper_model is None:
            self.__piper_model = PiperModel(os.fspath(self.model_path), os.fspath(self.config_path))
        return self.__piper_model

    def phonemize_text(self, text):
        return self.model.text_to_phonemes(text)

    def synthesize(self, text, speaker, rate):
        phonemes = self.phonemize_text(text)
        length_scale = self.config.length_scale
        if rate != DEFAULT_RATE:
            rate = rate or 1
            length_scale = length_scale * (50/rate)
            # Cap length_scale at 2.0 to avoid horrifying  audio result
            length_scale = 2. if length_scale > 2 else length_scale
        speaker_id = None
        if self.config.num_speakers > 1:
            if speaker is None:
                speaker_id = 0
            else:
                speaker_id=self.config.speaker_id_map.get(speaker)
        return self.model.synthesize_to_audio_bytes(
            phonemes=phonemes,
            speaker_id=speaker_id,
            length_scale=length_scale
        )


@dataclass
class SpeechOptions:
    voice: PiperVoice
    speaker: Optional[str] = None
    rate: int = DEFAULT_RATE
    volume: int = DEFAULT_VOLUME
    pitch: int = 50

    def set_voice(self, voice: PiperVoice):
        self.voice = voice
        self.speaker = None

    def copy(self):
        return copy.copy(self)


@dataclass
class BookmarkTask:
    name: str


class AudioTask(ABC):

    @abstractmethod
    def generate_audio(self) -> bytes:
        """Generate audio."""


@dataclass
class SilenceTask(AudioTask):
    time_ms: int
    sample_rate: int

    def generate_audio(self):
        """Generate silence (16-bit mono at sample rate)."""
        num_samples = int((self.time_ms / 1000.0) * self.sample_rate)
        return bytes(num_samples * 2)



@dataclass
class PiperSpeechSynthesisTask(AudioTask):
    """A pending request to synthesize a token."""

    text: str
    speech_options: SpeechOptions

    def generate_audio(self):
        audio_bytes = self.speech_options.voice.synthesize(
            self.text,
            self.speech_options.speaker,
            self.speech_options.rate
        )
        volume = self.speech_options.volume
        if volume != DEFAULT_VOLUME:
            audio_bytes = audioop.mul(audio_bytes, 2, volume / 100.0)
        return audio_bytes


class PiperTextToSpeechSystem:

    def __init__(
        self,
        voices: Sequence[PiperVoice],
        speech_options: SpeechOptions=None
    ):
        self.voices = voices
        if speech_options is None:
            try:
                voice = self.voices[0]
            except IndexError:
                raise VoiceNotFoundError("No Piper voices found")
            self.speech_options = SpeechOptions(voice=voice)
        else:
            speech_options = speech_options

    def shutdown(self):
        pass

    @property
    def voice(self) -> str:
        """Get the current voice key"""
        return self.speech_options.voice.key

    @voice.setter
    def voice(self, new_voice: str):
        """Set the current voice key"""
        for voice in self.voices:
            if voice.key == new_voice:
                self.speech_options.set_voice(voice)
                return
        raise VoiceNotFoundError(f"A voice with the given key `{new_voice}` was not found")

    @property
    def language(self) -> str:
        """Get the current voice language"""
        return self.speech_options.voice.language

    @language.setter
    def language(self, new_language: str):
        """Set the current voice language"""
        for voice in self.voices:
            if voice.language == new_language:
                self.speech_options.set_voice(voice)
                return
        raise VoiceNotFoundError(f"A voice with the given language `{new_language}` was not found")

    @property
    def volume(self) -> int:
        """Get the current volume in [0, 100]"""
        return self.speech_options.volume

    @volume.setter
    def volume(self, new_volume: int):
        """Set the current volume in [0, 100]"""
        self.speech_options.volume = new_volume

    @property
    def rate(self) -> int:
        """Get the current speaking rate in [0, 100]"""
        return self.speech_options.rate

    @rate.setter
    def rate(self, new_rate: int):
        """Set the current speaking rate in [0, 100]"""
        self.speech_options.rate = new_rate

    @property
    def pitch(self) -> int:
        """Get the current speaking rate in [0, 100]"""
        return self.speech_options.pitch

    @pitch.setter
    def pitch(self, new_pitch: int):
        """Set the current speaking rate in [0, 100]"""
        self.speech_options.pitch = new_pitch

    def get_voices(self):
        return self.voices

    def create_speech_task(self, text):
        return PiperSpeechSynthesisTask(
            text,
            self.speech_options.copy()
        )

    def create_break_task(self, time_ms):
        return SilenceTask(time_ms, self.speech_options.voice.config.sample_rate)

    def create_bookmark_task(self, name):
        return BookmarkTask(name)

    @staticmethod
    def load_voices_from_directory(voices_directory, *, directory_name_prefix="voice-"):
        rv = []
        for directory in (d for d in Path(voices_directory).iterdir() if d.is_dir()):
            if not directory.name.startswith(directory_name_prefix):
                continue
            *lang_components, name, quality = directory.name[len(directory_name_prefix):].split("-")
            lang = "-".join(lang_components) if len(lang_components) > 1 else lang_components[0]
            rv.append(
                PiperVoice(
                    key=f"{lang}-{name}-{quality}",
                    name=name.title(),
                    language=lang,
                    description="",
                    location=directory.absolute(),
                    properties={"quality": quality}
                )
            )
        return rv



@dataclass
class PiperConfig:
    num_symbols: int
    num_speakers: int
    sample_rate: int
    espeak_voice: str
    length_scale: float
    noise_scale: float
    noise_w: float
    phoneme_id_map: Mapping[str, Sequence[int]]
    speaker_id_map: Mapping[str, int]

    @classmethod
    def load_from_json_file(cls, config_path: Union[str, Path]):
        with open(config_path, "r", encoding="utf-8") as config_file:
            config_dict = json.load(config_file)
            inference = config_dict.get("inference", {})

            return cls(
                num_symbols=config_dict["num_symbols"],
                num_speakers=config_dict["num_speakers"],
                sample_rate=config_dict["audio"]["sample_rate"],
                espeak_voice=config_dict["espeak"]["voice"],
                noise_scale=inference.get("noise_scale", 0.667),
                length_scale=inference.get("length_scale", 1.0),
                noise_w=inference.get("noise_w", 0.8),
                phoneme_id_map=config_dict["phoneme_id_map"],
                speaker_id_map=config_dict["speaker_id_map"],
            )


class PiperModel:
    def __init__(
        self,
        model_path: Union[str, Path],
        config_path: Optional[Union[str, Path]] = None,
        use_cuda: bool = False,
    ):
        if config_path is None:
            config_path = f"{model_path}.json"

        self.config = PiperConfig.load_from_json_file(config_path)
        self.phonemizer = Phonemizer(
            self.config.espeak_voice,
        )

        session_options = onnxruntime.SessionOptions()
        session_options.enable_cpu_mem_arena = True
        session_options.enable_mem_pattern = True
        session_options.enable_mem_reuse = True
        session_options.execution_order = onnxruntime.ExecutionOrder.PRIORITY_BASED
        session_options.execution_mode = onnxruntime.ExecutionMode.ORT_PARALLEL
        session_options.enable_profiling = False
        session_options.inter_op_num_threads = int(os.cpu_count() / 2)
        session_options.intra_op_num_threads = int(os.cpu_count() / 2)

        self.model = onnxruntime.InferenceSession(
            str(model_path),
            sess_options=session_options,
            providers=["CPUExecutionProvider"]
            if not use_cuda
            else ["CUDAExecutionProvider"],
        )

    def synthesize_to_audio_bytes(
        self,
        phonemes: str,
        speaker_id: Optional[int] = None,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
    ) -> bytes:
        """Synthesize frameless WAV audio from text."""
        if length_scale is None:
            length_scale = self.config.length_scale

        if noise_scale is None:
            noise_scale = self.config.noise_scale

        if noise_w is None:
            noise_w = self.config.noise_w

        phoneme_id_map = self.config.phoneme_id_map
        _pad = self.config.phoneme_id_map[_PAD]
        phoneme_ids: List[int] = []
        for phoneme in (p for p in phonemes if p in phoneme_id_map):
            phoneme_ids.extend(phoneme_id_map[phoneme])
            phoneme_ids.extend(_pad)
        phoneme_ids.extend(self.config.phoneme_id_map[_EOS])
        phoneme_ids_array = np.expand_dims(np.array(phoneme_ids, dtype=np.int64), 0)
        phoneme_ids_lengths = np.array([phoneme_ids_array.shape[1]], dtype=np.int64)
        scales = np.array(
            [noise_scale, length_scale, noise_w],
            dtype=np.float32,
        )
        if (self.config.num_speakers > 1) and (speaker_id is not None):
            # Default speaker
            speaker_id = 0
        sid = None
        if speaker_id is not None:
            sid = np.array([speaker_id], dtype=np.int64)
        # Synthesize through Onnx
        audio = self.model.run(
            None,
            {
                "input": phoneme_ids_array,
                "input_lengths": phoneme_ids_lengths,
                "scales": scales,
                "sid": sid,
            },
        )[0].squeeze((0, 1))
        audio = self.audio_float_to_int16(audio.squeeze())
        return audio.tobytes()

    def synthesize_to_wav(
        self,
        text: str,
        speaker_id: Optional[int] = None,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
    ):
        audio_bytes = self.synthesize_to_audio_bytes(text, speaker_id, length_scale, noise_scale, noise_w)
        # Convert to WAV
        with io.BytesIO() as wav_io:
            wav_file: wave.Wave_write = wave.open(wav_io, "wb")
            with wav_file:
                wav_file.setframerate(self.config.sample_rate)
                wav_file.setsampwidth(2)
                wav_file.setnchannels(1)
                wav_file.writeframes(audio_bytes)
            return wav_io.getvalue()

    def text_to_phonemes(self, text, text_language=None):
        # RStrip `.` character from the end of the text because it causes unusual audio output
        text = text.rstrip(".")
        phonemes_str = self.phonemizer.phonemize(text, keep_clause_breakers=True)
        phonemes = [_BOS] + list(phonemes_str)
        return phonemes

    def word_to_phonemes(self, word_text, word_role=None, text_language=None):
        return self.text_to_phonemes(word_text, text_language=text_language)

    def say_as_to_phonemes(self, text, interpret_as, say_format=None, text_language=None):
        return self.text_to_phonemes(text, text_language=text_language)

    @staticmethod
    def audio_float_to_int16(
        audio: np.ndarray, max_wav_value: float = 32767.0
    ) -> np.ndarray:
        """Normalize audio and convert to int16 range"""
        audio_norm = audio * (max_wav_value / max(0.01, np.max(np.abs(audio))))
        audio_norm = np.clip(audio_norm, -max_wav_value, max_wav_value)
        audio_norm = audio_norm.astype("int16")
        return audio_norm


