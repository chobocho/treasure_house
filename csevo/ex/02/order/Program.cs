// 슬라이드 p2-v1-order — 피연산자는 왼쪽에서 오른쪽으로, C# 1.0
using System;

class App
{
    static int Log(string name, int v)
    {
        Console.Write(name + " ");
        return v;
    }

    static void Show(int a, int b, int c)
    {
        Console.WriteLine("-> " + a + " " + b + " " + c);
    }

    static void Main()
    {
        int r = Log("A", 1) + Log("B", 2) * Log("C", 3);
        Console.WriteLine("= " + r);              // * first, A first

        int i = 1;
        Show(i, i++, i);                          // 1 1 2
        i = 1;
        i = i++ + ++i;                            // 1 + 3
        Console.WriteLine("i = " + i);
        int[] a = { 10, 20, 30 };
        int k = 0;
        a[k] = k = 2;                             // a[0] = 2
        Console.WriteLine(a[0] + " " + a[2] + " " + k);
    }
}
