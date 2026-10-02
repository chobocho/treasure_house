// 슬라이드 p9-v8-unmanagedgen — 비관리 생성 형식, C# 8.0
using System;

struct Coords<T>
{
    public T X;
    public T Y;
}

class App
{
    static unsafe void Main()
    {
        Span<Coords<int>> cs = stackalloc[]
        {
            new Coords<int> { X = 0, Y = 0 },
            new Coords<int> { X = 0, Y = 3 },
            new Coords<int> { X = 4, Y = 0 },
        };
        Console.WriteLine(sizeof(Coords<int>) + " "
            + sizeof(Coords<long>));

        Coords<int> c = cs[2];
        Coords<int>* p = &c;                 // a pointer to it
        p->Y = 3;
        Console.WriteLine(c.X + "," + c.Y);
    }
}
