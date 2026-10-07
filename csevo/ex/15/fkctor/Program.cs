// 슬라이드 p15-v14-fk-ctor — 생성자의 대입은 setter 로, C# 14
using System;

class C
{
    public C()
    {
        P1 = 1;   // no setter: assigns the backing field
        P2 = 2;   // no setter: assigns the backing field
        P3 = 3;   // calls P3's setter
        P4 = 4;   // calls P4's setter
    }

    int P1 => field;
    int P2 { get => field; }
    int P3 { get => field; set { Log("P3"); field = value; } }
    int P4 { get => field; set { Log("P4"); field = value * 10; } }

    static void Log(string s) => Console.WriteLine("  set " + s);

    static void Main()
    {
        var c = new C();
        Console.WriteLine(c.P1 + " " + c.P2 + " " + c.P3 + " " + c.P4);
#if BAD
        c.P1 = 5;
#endif
    }
}
