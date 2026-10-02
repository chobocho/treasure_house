// 슬라이드 p9-v8-dim-state — 인스턴스 상태는 없다, C# 8.0
using System;

interface IStore
{
    static int shared = 1;            // static field: allowed
    int Size { get; set; }            // abstract property: allowed
#if BAD
    int count;                        // instance field
    int Max { get; set; } = 10;       // auto-property with a value
#endif
}

class Box : IStore
{
    public int Size { get; set; }
}

class App
{
    static void Main()
    {
        IStore s = new Box { Size = 3 };
        Console.WriteLine(s.Size + IStore.shared);
    }
}
