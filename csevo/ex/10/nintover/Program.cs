// 슬라이드 p10-v9-nint-over — nint 와 IntPtr 는 한 형식, C# 9.0
using System;

class App
{
    static string M(nint n) => "M(nint " + n + ")";
#if OVER
    static string M(IntPtr p) => "M(IntPtr)";
#endif
#if ENUM
    enum E : nint { A }
#endif

    static void Main()
    {
        IntPtr p = (IntPtr)5;
        Console.WriteLine(M(p));             // IntPtr goes to M(nint)
        object[] arr = { "a", "b", "c" };
        nint i = 2;
        Console.WriteLine(arr[i]);           // index without conversion
    }
}
