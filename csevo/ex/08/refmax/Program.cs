// 슬라이드 p8-v7-ref-max — 둘 중 큰 쪽의 자리를 돌려준다, C# 7.0
using System;

class App
{
    // ref parameters may be returned: they outlive this frame
    static ref int Max(ref int a, ref int b)
    {
        if (a >= b) return ref a;
        return ref b;
    }

    static void Main()
    {
        int x = 3, y = 8;
        Max(ref x, ref y) = 0;          // zero the larger one
        Console.WriteLine(x + " " + y);
        Max(ref x, ref y) += 10;        // now x (3) is the larger
        Console.WriteLine(x + " " + y);
#if BAD
        ref int m = ref (x > y ? ref x : ref y);   // ref ?:
#endif
    }
}
