// 슬라이드 p15-v14-nm-old — 쓰지도 않을 형식 인수를 고르던 때, C# 13
using System;

abstract class Shape { }

class Registry<T> where T : Shape, new()
{
    public static int Count = 0;
}

class DummyShape : Shape { }      // exists only to feed nameof

class Program
{
    static void Main()
    {
#if OBJ
        Console.WriteLine(nameof(Registry<object>));
#endif
#if ABS
        Console.WriteLine(nameof(Registry<Shape>));
#endif
        Console.WriteLine(nameof(Registry<DummyShape>));
#if CS14
        Console.WriteLine(nameof(Registry<>.Count));
#endif
    }
}
