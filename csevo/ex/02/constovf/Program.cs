// 슬라이드 p2-v1-constovf — 상수식의 넘침은 컴파일 오류, C# 1.0
using System;

class App
{
    static void Main()
    {
        int a = int.MaxValue + 1;             // constant: checked
        int b = unchecked(int.MaxValue + 1);  // allowed: -2147483648
        byte c = 300;                         // constant out of range
        byte d = (byte)300;                   // cast of a constant
        int e = 1 / 0;                        // constant division
        Console.WriteLine(a + b + c + d + e);
    }
}
