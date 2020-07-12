using OcPromptBuilder;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Windows.Foundation;
using Windows.Foundation.Metadata;
using Windows.Media.Core;
using Windows.Media.Playback;
using Windows.Media.SpeechSynthesis;
using Windows.Storage;
using Windows.Storage.Streams;

// Reference implementation: NVDA screen reader <https://github.com/nvaccess/nvda>.

namespace OcSpeechEngine
{

    public enum OcSynthState { Ready = 0, Busy = 1, Paused = 2 };

    public struct OnecoreVoiceInfo : IComparable<OnecoreVoiceInfo>
    {
        public string Name { get; private set; }
        public string Description { get; private set; }
        public string Id { get; private set; }
        public string Language { get; private set; }

        public OnecoreVoiceInfo(string name, string description, string id, string language)
        {
            Name = name;
            Description = description;
            Id = id;
            Language = language;
        }

        public int CompareTo(OnecoreVoiceInfo other)
        {
            return string.Compare(Name, other.Name);
        }

        public override bool Equals(object obj)
        {
            if (!(obj is OnecoreVoiceInfo))
                return false;
            OnecoreVoiceInfo voice = (OnecoreVoiceInfo)obj;
            return Id.Equals((voice.Id));
        }
        public override int GetHashCode()
        {
            return Id.GetHashCode();
        }
    }

    public class OcSpeechEngine
    {
        private readonly SpeechSynthesizer synth = new SpeechSynthesizer();
        private readonly MediaPlayer player = new MediaPlayer();
        private string currentVoiceId;
        private OcSynthState state = OcSynthState.Ready;
        private readonly ConcurrentDictionary<int, SpeechSynthesisStream> presynthesizedText = new ConcurrentDictionary<int, SpeechSynthesisStream>();
        private OcPromptBuilder.OcPromptBuilder CurrentPrompt;
        public static readonly bool IsProsodySupported = ApiInformation.IsApiContractPresent("Windows.Foundation.UniversalApiContract", 5, 0);
        public event TypedEventHandler<OcSpeechEngine, OcSynthState> StateChanged;
        public event TypedEventHandler<OcSpeechEngine, string> BookmarkReached;
        public event TypedEventHandler<OcSpeechEngine, string> VoiceChanged;
        public OcSynthState State
        {
            get
            {
                return state;
            }
            private set
            {
                state = value;
                if (StateChanged != null)
                    Parallel.Invoke(() => StateChanged(this, value));
            }
        }
        public OnecoreVoiceInfo Voice
        {
            get
            {
                return (
                        from v in GetVoices()
                        where v.Id.Equals(currentVoiceId)
                        select v).Single();
            }
            set
            {
                if (value.Id.Equals(currentVoiceId))
                    return;
                VoiceInformation voice = GetVoiceById(value.Id);
                synth.Voice = voice;
                currentVoiceId = value.Id;
                if (VoiceChanged != null)
                    Parallel.Invoke(() => VoiceChanged(this, value.Id));
            }
        }
        public double Rate
        {
            get
            {
                if (!IsProsodySupported)
                    throw new NotSupportedException("Rate option is not supported in this API version");
                return synth.Options.SpeakingRate / 0.06;
            }
            set
            {
                if (!IsProsodySupported)
                    throw new NotSupportedException("Rate option is not supported in this API version");
                synth.Options.SpeakingRate = value * 0.06;
            }
        }
        public double Volume
        {
            get
            {
                return player.Volume * 100;
            }
            set
            {
                if (value < 0 || value > 100)
                    throw new ArgumentException("Volume level is out of range");
                player.Volume = value / 100;
            }
        }

        public OcSpeechEngine()
        {
            currentVoiceId = synth.Voice.Id;
            player.AutoPlay = true;
            player.MediaEnded += OnMediaEnded;
            player.MediaFailed += OnPlayerMediaFaild;
            if (ApiInformation.IsPropertyPresent("Windows.Media.Playback.MediaPlayer", "PlaybackSession"))
            {
                player.PlaybackSession.PlaybackStateChanged += OnPlaybackStateChanged;
            }
            else
            {
                player.CurrentStateChanged += OnPlaybackStateChanged;
            }
            // Remove the scilence after speech utterance
            if ApiInformation.IsApiContractPresent("Windows.Foundation.UniversalApiContract", 6, 0))
                synth.Options.AppendedSilence = SpeechAppendedSilence.Min;
        }

        ~OcSpeechEngine()
        {
            player.Dispose();
        }
        public void Close()
        {
            CancelSpeech();
            if (ApiInformation.IsPropertyPresent("Windows.Media.Playback.MediaPlayer", "PlaybackSession"))
            {
                player.PlaybackSession.PlaybackStateChanged -= OnPlaybackStateChanged;
            }
            else
            {
                player.CurrentStateChanged -= OnPlaybackStateChanged;
            }
            player.MediaEnded -= OnMediaEnded;
            player.MediaFailed -= OnPlayerMediaFaild;
            State = OcSynthState.Ready;
        }

        public IEnumerable<OnecoreVoiceInfo> GetVoices()
        {
            List<OnecoreVoiceInfo> voiceList = new List<OnecoreVoiceInfo>();
            foreach (VoiceInformation vc in SpeechSynthesizer.AllVoices)
            {
                OnecoreVoiceInfo voice = new OnecoreVoiceInfo(vc.DisplayName, vc.Description, vc.Id, vc.Language);
                voiceList.Add(voice);
            }
            voiceList.Sort();
            return voiceList;
        }

        public void SelectVoice(string voiceId)
        {
            OnecoreVoiceInfo voice = (
                from vinfo in GetVoices()
                where vinfo.Id.Equals(voiceId)
                select vinfo).Single();
            Voice = voice;
        }

        private VoiceInformation GetVoiceById(string voiceId)
        {
            return (
                 from v in SpeechSynthesizer.AllVoices
                 where v.Id.Equals(voiceId)
                 select v).Single();
        }

        private void Stop()
        {
            player.Pause();
            player.Source = MediaSource.CreateFromStream(new InMemoryRandomAccessStream(), "");
            State = OcSynthState.Ready;
        }

        public void Pause()
        {
            if (State.Equals(OcSynthState.Busy))
            {
                player.Pause();
                State = OcSynthState.Paused;
            }
        }

        public void Resume()
        {
            if (State.Equals(OcSynthState.Paused))
            {
                player.Play();
                State = OcSynthState.Busy;
            }
        }

        public void CancelSpeech()
        {
            Stop();
            presynthesizedText.Clear();
            CurrentPrompt?.Clear();
        }

        public async Task SpeakAsync(OcPromptBuilder.OcPromptBuilder prompt)
        {
            CancelSpeech();
            foreach (SpeechElement element in prompt.speechQueue)
            {
                Parallel.Invoke(() => PreSynthesizeText(element));
            }
            CurrentPrompt = prompt;
            await ProcessSpeechPrompt();
        }

        private void PreSynthesizeText(SpeechElement element)
        {
            if (element.Kind.Equals(SpeechElementKind.Text) || element.Kind.Equals(SpeechElementKind.Ssml))
            {
                synth.SynthesizeSsmlToStreamAsync(element.Content).AsTask<SpeechSynthesisStream>().ContinueWith((result) =>
                {
                    presynthesizedText.TryAdd(element.Content.GetHashCode(), result.Result);
                });
            }
        }

        private async Task Synthesize(string content, bool isSsml = false)
        {
            SpeechSynthesisStream stream;
            if (presynthesizedText.ContainsKey(content.GetHashCode()))
            {
                presynthesizedText.TryRemove(content.GetHashCode(), out stream);
            }
            else if (isSsml)
            {
                stream = await synth.SynthesizeSsmlToStreamAsync(content);
            }
            else
            {
                stream = await synth.SynthesizeTextToStreamAsync(content);
            }
            player.Source = MediaSource.CreateFromStream(stream, stream.ContentType);
            State = OcSynthState.Busy;
        }

        private async Task ProcessSpeechPrompt()
        {
            SpeechElement speechelm;
            CurrentPrompt.speechQueue.TryDequeue(out speechelm);
            switch (speechelm.Kind)
            {
                case SpeechElementKind.Text:
                    await Synthesize(speechelm.Content);
                    break;
                case SpeechElementKind.Ssml:
                    await Synthesize(speechelm.Content, true);
                    break;
                case SpeechElementKind.Bookmark:
                    if (BookmarkReached != null)
                        Parallel.Invoke(() => BookmarkReached(this, speechelm.Content));
                    await ProcessSpeechPrompt();
                    break;
                case SpeechElementKind.Audio:
                    StorageFile file = await StorageFile.GetFileFromPathAsync(speechelm.Content);
                    player.Source = MediaSource.CreateFromStorageFile(file);
                    State = OcSynthState.Busy;
                    break;
                default:
                    throw new InvalidOperationException("Unplayable item");
            }
        }

        private OcSynthState PlayerStateToSynthState(MediaPlaybackState state)
        {
            if (state == MediaPlaybackState.Buffering || state == MediaPlaybackState.Opening || state == MediaPlaybackState.Playing)
            {
                return OcSynthState.Busy;
            }
            else if (state == MediaPlaybackState.Paused)
            {
                return OcSynthState.Paused;
            }
            else
            {
                return OcSynthState.Ready;
            }
        }

        private void OnPlaybackStateChanged(MediaPlaybackSession session, object args)
        {
            ChangeState();
        }
        private void OnPlaybackStateChanged(MediaPlayer plyer, object args)
        {
            ChangeState();
        }
        private void ChangeState()
        {
            OcSynthState playerState = PlayerStateToSynthState(player.PlaybackSession.PlaybackState);
            if (playerState != State && StateChanged != null)
                State = playerState;
        }

        private void OnMediaEnded(MediaPlayer sender, object args)
        {
            State = OcSynthState.Ready;
            ProcessSpeechPrompt().RunSynchronously();
        }

        private void OnPlayerMediaFaild(MediaPlayer sender, object args)
        {
            State = OcSynthState.Ready;
        }

    }
}