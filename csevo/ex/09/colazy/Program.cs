// 슬라이드 p9-v8-co-lazy — 오른쪽은 null 일 때만, C# 8.0
using System;

class App
{
    static int made, indexed;
    static string[] slots = new string[1];

    static string Make() { made++; return "made"; }
    static int Slot() { indexed++; return 0; }

    static void Main()
    {
        string s = null;
        s ??= Make();
        s ??= Make();                         // s is not null: no call
        Console.WriteLine(s + ", Make called " + made);

        slots[Slot()] ??= "a";
        Console.WriteLine(slots[0] + ", index evaluated " + indexed);

        indexed = 0;                          // the hand-written form
        slots[Slot()] = slots[Slot()] ?? "c";
        Console.WriteLine(slots[0] + ", index evaluated " + indexed);
    }
}
