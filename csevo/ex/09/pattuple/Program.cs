// 슬라이드 p9-v8-tuplepat — 튜플 패턴, C# 8.0
using System;

enum Hand { Rock, Paper, Scissors }

class App
{
    // who wins? two inputs, one switch
    static string Judge(Hand a, Hand b) => (a, b) switch
    {
        (Hand.Rock, Hand.Scissors) => "A: rock breaks scissors",
        (Hand.Paper, Hand.Rock) => "A: paper wraps rock",
        (Hand.Scissors, Hand.Paper) => "A: scissors cut paper",
        var (x, y) when x == y => "draw",
        _ => "B wins",
    };

    static void Main()
    {
        Hand[] all = { Hand.Rock, Hand.Paper, Hand.Scissors };
        foreach (Hand a in all)
            foreach (Hand b in all)
                Console.WriteLine("{0,-8} {1,-8} {2}",
                    a, b, Judge(a, b));
    }
}
