// 슬라이드 p9-v8-switchexpr — switch 식, C# 8.0
using System;

enum Light { Red, Yellow, Green }

class App
{
    // one arm per line: pattern => expression
    static Light Next(Light now) =>
        now switch
        {
            Light.Red    => Light.Green,
            Light.Green  => Light.Yellow,
            Light.Yellow => Light.Red,
            _            => throw new ArgumentException("bad light"),
        };

    static int Seconds(Light l) => l switch
    {
        Light.Red => 30,
        Light.Yellow => 3,
        _ => 25,
    };

    static void Main()
    {
        Light l = Light.Red;
        for (int i = 0; i < 4; i++)
        {
            Console.WriteLine("{0,-6} {1,2}s", l, Seconds(l));
            l = Next(l);
        }
    }
}
