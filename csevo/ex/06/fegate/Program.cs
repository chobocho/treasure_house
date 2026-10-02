// 슬라이드 p6-v5-foreach — foreach 변수 포착의 변화, C# 5.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        int[] items = { 1, 2, 3 };
        List<Func<int>> fs = new List<Func<int>>();
        foreach (int x in items)
        {
            fs.Add(() => x);
        }
        foreach (Func<int> f in fs)
        {
            Console.Write(f() + " ");
        }
        Console.WriteLine();
    }
}
