// 슬라이드 p3-v2-anon-static — static 이면 잡지 못한다, C# 9
using System;

delegate int Op(int x);

class App
{
    static void Main()
    {
        int k = 3;
        Op times = static delegate(int x) { return x * k; };
    }
}
