// 슬라이드 p12-v11-raw-u8 — 원시 문자열에 u8 을 붙이면, C# 11.0
using System;
using System.Text;

class App
{
    static void Main()
    {
        ReadOnlySpan<byte> req = """
            GET / HTTP/1.1
            Host: example.org

            """u8;
        Console.WriteLine(req.Length + " bytes");
        string text = Encoding.UTF8.GetString(req);
        Console.WriteLine(text.Replace("\n", "|"));
#if INTERP
        string host = "example.org";
        ReadOnlySpan<byte> bad = $"""Host: {host}"""u8;
#endif
    }
}
