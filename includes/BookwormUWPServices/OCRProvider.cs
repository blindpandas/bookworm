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
        private readonly OcrEngine engine;

        public OCRProvider(string language)
        {
            engine = OcrEngine.TryCreateFromLanguage(new Language(language));
        }

        public static List<string> GetRecognizableLanguages()
        {
            List<string> langs = new List<string>();
            foreach (Language lang in OcrEngine.AvailableRecognizerLanguages)
                langs.Add(lang.LanguageTag);
            return langs;
        }

        public List<string> Recognize(Byte[] image, int width, int height)
        {
            IBuffer buf = CryptographicBuffer.CreateFromByteArray(image);
            SoftwareBitmap sbitmap = SoftwareBitmap.CreateCopyFromBuffer(buf, BitmapPixelFormat.Bgra8, width, height);
            Task<OcrResult> task = engine.RecognizeAsync(sbitmap).AsTask();
            task.Wait();
            OcrResult result = task.Result;
            List<string> lines = new List<string>();
            foreach (OcrLine line in result.Lines)
                lines.Add(line.Text);
            return ProcessLines(lines);
        }

        private List<string> ProcessLines(List<string> lines)
        {
            if (engine.RecognizerLanguage.LayoutDirection == LanguageLayoutDirection.Rtl)
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
