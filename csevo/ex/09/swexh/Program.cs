// 슬라이드 p9-v8-switchexpr-exh — 빠뜨린 갈래, C# 8.0
using System;

enum Suit { Spade, Heart, Diamond, Club }

class App
{
    // Club is missing: a warning at compile time, not an error
    static char Symbol(Suit s) => s switch
    {
        Suit.Spade => 'S',
        Suit.Heart => 'H',
        Suit.Diamond => 'D',
    };

    static void Main()
    {
        foreach (Suit s in Enum.GetValues(typeof(Suit)))
            Console.WriteLine("{0} {1}", s, Symbol(s));
    }
}
