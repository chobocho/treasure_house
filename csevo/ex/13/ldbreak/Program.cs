// 슬라이드 p13-v12-ld-break — 깨지는 변경: var 와 메서드 그룹, C# 12
using System;

class Program
{
    static void WriteInt(int i = 0) { Console.WriteLine(i); }
    static int Count(params int[] xs) => xs.Length;

    static void DoAction(Action<int> a, int p) { a(p); }
    static int DoFunction(Func<int[], int> f, int p) => f(new[] { p });

    static void Main()
    {
        var writeInt = WriteInt;
        var counter = Count;
        Console.WriteLine(writeInt.GetType().Name);
#if BAD
        DoAction(writeInt, 3);
#endif
#if BAD2
        Console.WriteLine(DoFunction(counter, 3));
#endif
        DoAction(WriteInt, 3);          // no var: still converts
        Console.WriteLine(DoFunction(Count, 3));
    }
}
