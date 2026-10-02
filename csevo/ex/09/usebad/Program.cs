// 슬라이드 p9-v8-ud-bad — using 선언을 못 쓰는 곳, C# 8.0
using System;
using System.IO;

class App
{
    static void Main(string[] args)
    {
        switch (args.Length)
        {
            case 0:
                using var s = new MemoryStream();   // needs braces
                break;
        }

        using var t;                                // needs a value
        using var u = new MemoryStream();
        u = new MemoryStream();                     // read-only
        using var n = 42;                           // not disposable
    }
}
