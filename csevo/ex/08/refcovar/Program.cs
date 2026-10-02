// 슬라이드 p8-v7-ref-covar — 공변 배열의 원소를 ref 로 잡으면, C# 7.0
using System;

class App
{
    static ref T At<T>(T[] items, int i) { return ref items[i]; }

    static void Main()
    {
        string[] names = { "a", "b" };
        ref string s = ref At(names, 0);     // T = string: fine
        s = "z";
        Console.WriteLine(names[0]);

        object[] objs = names;               // array covariance (C# 1)
        objs[1] = "y";                       // a store: checked, ok
        Console.WriteLine(names[1]);
        try
        {
            ref object o = ref objs[0];      // an address: checked too
            Console.WriteLine("got a ref");
        }
        catch (ArrayTypeMismatchException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
