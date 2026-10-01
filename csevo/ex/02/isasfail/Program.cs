// 슬라이드 p2-v1-isasfail — as 는 값 형식에 못 쓴다, C# 1.0
using System;

class App
{
    static void Main()
    {
        object n = 42;
        int i = n as int;                         // value type
        if (n is int j)                           // C# 7 pattern
        {
            Console.WriteLine(i + j);
        }
    }
}
