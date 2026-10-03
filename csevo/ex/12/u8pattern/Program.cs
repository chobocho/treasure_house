// 슬라이드 p12-v11-utf8-pattern — u8 은 패턴이 될 수 없다, C# 11.0
using System;

class App
{
    static string Verb(ReadOnlySpan<byte> v)
    {
        if (v.SequenceEqual("GET"u8)) return "get";
        if (v.SequenceEqual("PUT"u8)) return "put";
        return "other";
    }

    static void Main()
    {
        ReadOnlySpan<byte> line = "PUT /x"u8;
        Console.WriteLine(Verb(line[..3]) + " " + Verb(line[4..]));
#if IS
        Console.WriteLine(line[..3] is "PUT"u8);
#endif
#if SWITCH
        string s = line[..3] switch { "PUT"u8 => "put", _ => "?" };
#endif
    }
}
