// 슬라이드 p8-v7-ref-alias — ref 는 배열 변수가 아니라 원소를, C# 7.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        int[] a = { 1, 2, 3 };
        ref int first = ref a[0];
        Array.Resize(ref a, 4);      // copies into a new array
        first = 100;                 // writes into the OLD array
        Console.WriteLine(string.Join(",", a));

        int[] keep = a;
        ref int x = ref a[1];
        a = new int[] { 7, 8, 9 };   // the variable moves on
        x = 200;                     // keep[1] changes, a does not
        Console.WriteLine(string.Join(",", a) + " / " +
            string.Join(",", keep));
#if BAD
        var list = new List<int> { 1, 2 };
        ref int y = ref list[0];     // List<T> indexer returns a copy
#endif
    }
}
