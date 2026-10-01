// 슬라이드 p3-v2-generics-safety — 잘못 넣으면 컴파일 오류, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<int> xs = new List<int>();
        xs.Add(1);
        xs.Add("3");                      // rejected at compile time
        string s = xs[0];                 // so is a wrong read
        Console.WriteLine(s);
    }
}
