// 슬라이드 p3-v2-generics-why — 제네릭 이전의 ArrayList, C# 1.0
using System;
using System.Collections;

class App
{
    static int Sum(ArrayList xs)
    {
        int total = 0;
        foreach (object o in xs)
        {
            total += (int)o;              // a cast on every element
        }
        return total;
    }

    static void Main()
    {
        ArrayList xs = new ArrayList();
        xs.Add(1);
        xs.Add(2);
        Console.WriteLine(Sum(xs));
        xs.Add("3");                      // compiles: Add takes object
        Console.WriteLine(Sum(xs));       // fails only at run time
    }
}
