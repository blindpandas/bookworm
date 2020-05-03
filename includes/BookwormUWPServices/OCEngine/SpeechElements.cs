using System.Collections.Concurrent;

namespace OcPromptBuilder
{

    internal enum SpeechElementKind
    {
        Text = 0,
        Ssml = 2,
        Bookmark = 4,
        Audio = 8
    }

    internal struct SpeechElement
    {
        internal SpeechElementKind Kind { get; private set; }
        internal string Content { get; private set; }

        internal SpeechElement(SpeechElementKind kind, string content)
        {
            Kind = kind;
            Content = content;
        }
    }

    public class OcPromptBuilder
    {
        internal ConcurrentQueue<SpeechElement> speechQueue = new ConcurrentQueue<SpeechElement>();
        public void Clear()
        {
            while (!speechQueue.IsEmpty)
            {
                SpeechElement elm;
                speechQueue.TryDequeue(out elm);
            }
            speechQueue = new ConcurrentQueue<SpeechElement>();
        }
        public void AddText(string text)
        {
            speechQueue.Enqueue(new SpeechElement(SpeechElementKind.Text, text));
        }

        public void AddSsml(string ssml)
        {
            speechQueue.Enqueue(new SpeechElement(SpeechElementKind.Ssml, ssml));
        }

        public void AddBookmark(string bookmark)
        {
            speechQueue.Enqueue(new SpeechElement(SpeechElementKind.Bookmark, bookmark));
        }

        public void AddAudio(string filename)
        {
            speechQueue.Enqueue(new SpeechElement(SpeechElementKind.Audio, filename));
        }
    }
}
