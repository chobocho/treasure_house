// 슬라이드 p5-v4-var-array — 배열 공변(C# 1)과 안전한 변성, C# 4.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        string[] words = { "a", "b" };
        object[] arr = words;                 // array covariance
        IEnumerable<object> seq = words;      // generic covariance
        Console.WriteLine(string.Join(" ", seq));
        try
        {
            arr[0] = 42;                      // checked at run time
        }
        catch (ArrayTypeMismatchException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
        // seq has no Add: IEnumerable<T> can only hand out T
        IList<object> list = words;      // arrays implement IList<T>
        try { list[1] = 42; }
        catch (ArrayTypeMismatchException e)
        {
            Console.WriteLine("IList<object>: " + e.GetType().Name);
        }
    }
}
