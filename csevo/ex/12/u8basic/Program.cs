// 슬라이드 p12-v11-utf8 — UTF-8 문자열 리터럴, C# 11.0
using System;
using System.Text;

class App
{
    static void Dump(ReadOnlySpan<byte> bytes)
    {
        foreach (byte b in bytes)
            Console.Write(b.ToString("X2") + " ");
        Console.WriteLine($"({bytes.Length} bytes)");
    }

    static void Main()
    {
        var auth = "AUTH "u8;
        Dump(auth);
        Dump("가"u8);                      // one Hangul syllable
        Dump("é\r\n"u8);
        Console.WriteLine(Encoding.UTF8.GetString("가나"u8));
    }
}
