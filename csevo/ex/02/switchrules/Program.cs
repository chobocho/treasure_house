// 슬라이드 p2-v1-switchrules — switch 의 두 규칙, C# 1.0
using System;

class App
{
    static void Main()
    {
        int n = 1;
        switch (n)
        {
            case 1:
                Console.WriteLine("one");
            case 2:
                Console.WriteLine("two");
                break;
        }
        bool b = n > 0;
        switch (b)
        {
            case true: Console.WriteLine("yes"); break;
            case false: Console.WriteLine("no"); break;
        }
    }
}
