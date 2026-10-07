// 슬라이드 p15-v14-na-not — null 조건 대입이 안 되는 자리, C# 14
using System;

struct Point { public int X { get; set; } }

class Cell
{
    public int V = 0;
    int slot;
    public ref int Slot() => ref slot;
}

class Program
{
    static void Bump(ref int x) => x++;

    static void Main()
    {
        Cell c = new Cell(), d = null;
        c?.Slot() = 42;                     // ref return: allowed
        d?.Slot() = 43;
        Console.WriteLine(c.Slot());
#if STRUCT
        Point p = new Point();
        p?.X = 1;                           // non-nullable value type
#endif
#if NULLABLE
        Point? q = new Point();
        q?.X = 1;                           // q.Value is not a variable
#endif
#if REF
        Bump(ref c?.V);                     // still not an lvalue
#endif
#if DECON
        int y;
        (c?.V, y) = (1, 2);                 // no deconstruction
#endif
    }
}
