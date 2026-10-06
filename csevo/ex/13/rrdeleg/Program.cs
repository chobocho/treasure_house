// 슬라이드 p13-v12-rr-deleg — 람다·메서드 그룹 변환의 ref 종류, C# 12.0
using System;

delegate int DIn(in int p);
delegate int DRef(ref int p);
delegate int DRR(ref readonly int p);

class App
{
    static int ByRef(ref int p) => p;

    static void Main()
    {
        // allowed with warning CS9198
        DRef a = (in int p) => p + 1;
        DRR b = (in int p) => p + 2;
        DIn c = (ref readonly int p) => p + 3;
        DRef d = (ref readonly int p) => p + 4;
#if BAD
        DIn e = (ref int p) => p;  // ref target, in delegate
#elif BAD2
        DRR e = ByRef;             // ref target, rr delegate
#endif
        int x = 0;
        Console.WriteLine($"{a(ref x)} {b(in x)} {c(in x)} {d(ref x)}");
    }
}
