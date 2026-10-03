// 슬라이드 p12-v11-wave7 — 경고 웨이브 7: 소문자만인 형식 이름, C# 11.0
using System;

class point                    // all lower-case ASCII
{
    public int x;
}

#if REQ
class required { }             // a C# 11 keyword since then
#endif

class App
{
    static void Main()
    {
        var p = new point { x = 3 };
        Console.WriteLine(p.x);
    }
}
