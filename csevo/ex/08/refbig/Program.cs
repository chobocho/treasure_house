// 슬라이드 p8-v7-ref-big — 큰 구조체 배열의 원소를 그 자리에서, C# 7.0
using System;

struct Big
{
    public long A, B, C, D;      // 32 bytes copied on every read
}

class App
{
    static Big[] items = new Big[3];

    static Big Copy(int i) { return items[i]; }
    static ref Big Slot(int i) { return ref items[i]; }

    static void Main()
    {
        Big c = Copy(0);
        c.A = 1;                 // changes the copy only
        Slot(1).A = 2;           // changes items[1] itself
        ref Big b = ref Slot(2);
        b.A = 3;
        b.D = 4;
        foreach (Big x in items)
            Console.WriteLine("A={0} D={1}", x.A, x.D);
#if BAD
        Copy(0).A = 1;           // the return value is not a variable
#endif
    }
}
