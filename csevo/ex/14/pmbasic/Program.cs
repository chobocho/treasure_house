// 슬라이드 p14-v13-params — params 컬렉션, C# 13
using System;

class Program
{
    // the whats-new example, unchanged
    public static void Concat<T>(params ReadOnlySpan<T> items)
    {
        for (int i = 0; i < items.Length; i++)
        {
            Console.Write(items[i]);
            Console.Write(" ");
        }
        Console.WriteLine();
    }

    static void Main()
    {
        Concat(1, 2, 3);            // expanded form
        Concat("a");
        Concat<int>();              // empty span
        int[] arr = { 4, 5 };
        Concat<int>(arr);           // array -> ReadOnlySpan<int>
        Concat([6, .. arr]);        // collection expression
    }
}
