// 슬라이드 p8-v7-pat-const — 상수 패턴, C# 7.0
using System;

enum Color { Red, Green }

class App
{
    static void Test(object o)
    {
        string name = o == null ? "null" : o.GetType().Name;
        Console.WriteLine("{0,-6} is 5:{1,-5} is null:{2,-5}"
            + " is \"5\":{3,-5} is Green:{4}",
            name, o is 5, o is null, o is "5", o is Color.Green);
    }

    static void Main()
    {
        Test(5);
        Test(5L);           // a boxed long is not the int 5
        Test("5");
        Test(null);
        Test(Color.Green);
        long n = 5;
        Console.WriteLine(n is 5);          // integral: n == 5
    }
}
