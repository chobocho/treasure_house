// 슬라이드 p3-v2-anon-jump — 익명 메서드 밖으로 break, C# 2.0
using System;

delegate void Visit(int x);

class App
{
    static void Main()
    {
        for (int i = 0; i < 3; i++)
        {
            Visit v = delegate(int x) { if (x > 1) break; };
            v(i);
        }
    }
}
