// 슬라이드 p3-v2-closure-share — 값이 아니라 변수를 잡는다, C# 2.0
using System;

delegate void Setter(int value);
delegate int Getter();

class App
{
    static void Main()
    {
        int x = 0;
        Setter s = delegate(int value) { x = value; };
        Getter g = delegate { return x; };

        s(5);
        Console.WriteLine(g());          // 5: s and g share x
        x = 7;
        Console.WriteLine(g());          // 7: so does Main
        s(10);
        Console.WriteLine(x);            // 10
    }
}
