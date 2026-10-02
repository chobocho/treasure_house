// 슬라이드 p8-v7-ref — ref 반환과 ref 지역 변수, C# 7.0
using System;

class App
{
    // returns a reference to the element, not a copy of its value
    static ref int Find(int[,] m, int target)
    {
        for (int i = 0; i < m.GetLength(0); i++)
            for (int j = 0; j < m.GetLength(1); j++)
                if (m[i, j] == target)
                    return ref m[i, j];
        throw new InvalidOperationException("not found");
    }

    static void Main()
    {
        int[,] m = { { 1, 2 }, { 3, 42 } };
        ref int slot = ref Find(m, 42);   // a ref local
        slot = 7;                         // writes into m[1, 1]
        Console.WriteLine(m[1, 1]);
        Find(m, 3) = 30;                  // assign through the call
        Console.WriteLine(m[1, 0]);
    }
}
