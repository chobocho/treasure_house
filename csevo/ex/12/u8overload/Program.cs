// 슬라이드 p12-v11-utf8-overload — 오버로드를 고르는 접미사, C# 11.0
using System;
using System.Text;

class Writer
{
    public void Write(string s)
    {
        Console.Write("string → encode at run time: ");
        Write(Encoding.UTF8.GetBytes(s));
    }

    public void Write(ReadOnlySpan<byte> utf8) =>
        Console.WriteLine($"bytes({utf8.Length})");
}

class App
{
    static void Main()
    {
        var w = new Writer();
        w.Write("Content-Length: ");
        w.Write("Content-Length: "u8);
#if CAST
        w.Write((ReadOnlySpan<byte>)"Content-Length: ");
#endif
    }
}
