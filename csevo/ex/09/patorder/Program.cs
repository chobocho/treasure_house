// 슬라이드 p9-v8-pat-order — 가려진 갈래는 오류, C# 8.0
using System;

class App
{
    static string A(object o) => o switch
    {
        { } => "not null",
        string s => "string",            // CS8510: already handled
        _ => "null",
    };

    static string B(int n) => n switch
    {
        _ => "any",
        0 => "zero",                     // CS8510 again
    };

    static void C(object o)
    {
        switch (o)
        {
            case object x: break;
            case string s: break;        // statement: CS8120
        }
    }

    static void Main() { }
}
