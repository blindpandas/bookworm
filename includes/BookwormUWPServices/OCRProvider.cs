using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Windows.Globalization;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Security.Cryptography;
using Windows.Storage.Streams;


namespace OCRProvider
{

    public class OCRProvider
    {
        private readonly static Dictionary<string, OcrEngine> _engines = new Dictionary<string, OcrEngine>();

        public static List<string> GetRecognizableLanguages()
        {
            List<string> langs = new List<string>();
            foreach (Language lang in OcrEngine.AvailableRecognizerLanguages)
                langs.Add(lang.LanguageTag);
            return langs;
        }

        public static List<string> Recognize(string language, Byte[] image, int width, int height)
        {
            if (!_engines.ContainsKey(language))
                _engines.Add(language, OcrEngine.TryCreateFromLanguage(new Language(language)));
            OcrEngine engine = _engines[language];
            IBuffer buf = CryptographicBuffer.CreateFromByteArray(image);
            image = null;
            SoftwareBitmap sbitmap = SoftwareBitmap.CreateCopyFromBuffer(buf, BitmapPixelFormat.Bgra8, width, height);
            Task<OcrResult> task = engine.RecognizeAsync(sbitmap).AsTask();
            task.Wait();
            OcrResult result = task.Result;
            buf = null;
            GC.Collect();
            List<string> lines = new List<string>();
            foreach (OcrLine line in result.Lines)
                lines.Add(line.Text);
            return ProcessLines(lines, engine.RecognizerLanguage.LayoutDirection == LanguageLayoutDirection.Rtl);
        }

        private static List<string> ProcessLines(List<string> lines, bool isRtl)
        {
            if (isRtl)
            {
                // Problems with RTL languages
                List<string> revlines = new List<string>();
                foreach (string line in lines)
                {
                    IEnumerable<string> rline = line.Split(' ').Reverse();
                    revlines.Add(string.Join(" ", rline.ToArray()));
                }
                return revlines;
            }
            else
            {
                return lines;
            }
        }
    }
}
