// 슬라이드 p4-v3-lambda-loop — for 의 변수 하나를 함께 잡는다, C# 3.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<Func<int>> shared = new List<Func<int>>();
        for (int i = 0; i < 3; i++)
            shared.Add(() => i);

        List<Func<int>> copied = new List<Func<int>>();
        for (int i = 0; i < 3; i++)
        {
            int copy = i;                // a new variable per iteration
            copied.Add(() => copy);
        }

        foreach (Func<int> f in shared) Console.Write(f() + " ");
        Console.WriteLine();
        foreach (Func<int> f in copied) Console.Write(f() + " ");
        Console.WriteLine();
    }
}
