// 슬라이드 p10-v9-fnptr — 함수 포인터 delegate*, C# 9.0
using System;

unsafe class App
{
    static int Add(int a, int b) => a + b;
    static int Mul(int a, int b) => a * b;

    static int Apply(delegate*<int, int, int> f, int x, int y)
        => f(x, y);

    static void Main()
    {
        delegate*<int, int, int> p = &Add;
        Console.WriteLine(p(2, 3) + " " + Apply(&Mul, 4, 5));
        Func<int, int, int> d = Add;       // the delegate way
        Console.WriteLine(d(2, 3));
#if CMP
        Console.WriteLine(p == (delegate*<int, int, int>)&Add);
#endif
    }
}
