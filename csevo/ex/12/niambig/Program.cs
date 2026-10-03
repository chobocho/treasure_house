// 슬라이드 p12-v11-ni-ambig — UIntPtr + int 는 이제 모호하다, C# 11.0
using System;

class App
{
    static UIntPtr M(UIntPtr x, int y)
    {
#if BAD
        return x + y;          // was UIntPtr.operator +(UIntPtr, int)
#else
        return UIntPtr.Add(x, y) + unchecked((nuint)y);
#endif
    }

    static void Main() => Console.WriteLine(M(10, 3));
}
