// 슬라이드 p8-v7-pat-gate — is 의 형식 패턴, C# 7.0
using System;

class App
{
    static void Main()
    {
        object[] inputs = { 42, "hi", 2.5 };
        foreach (object o in inputs)
        {
            if (o is int n)                 // test and declare at once
                Console.WriteLine("int, doubled: " + n * 2);
            else
                Console.WriteLine("not an int: " + o);
        }
    }
}
