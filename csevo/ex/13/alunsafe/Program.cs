// 슬라이드 p13-v12-al-unsafe — 포인터 · 함수 포인터 별칭, C# 12.0
using System;
using unsafe IntPtrT = int*;
using unsafe BinOp = delegate*<int, int, int>;
#if NOUNSAFE
using Raw = byte*;
#endif

unsafe class App
{
    static int Add(int a, int b) => a + b;
    static int Mul(int a, int b) => a * b;

    static int Apply(BinOp op, int a, int b) => op(a, b);

    static void Main()
    {
        int v = 20;
        IntPtrT p = &v;
        *p += 1;
        Console.WriteLine(v);
        Console.WriteLine(Apply(&Add, 3, 4) + " " + Apply(&Mul, 3, 4));
    }
}
