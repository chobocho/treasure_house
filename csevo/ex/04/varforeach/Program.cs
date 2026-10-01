// 슬라이드 p4-v3-var-foreach — foreach 의 var, C# 3.0
using System;
using System.Collections;
using System.Collections.Generic;

class App
{
    static void Show(object o) { Console.WriteLine("object " + o); }
    static void Show(int i) { Console.WriteLine("int " + i); }

    static void Main()
    {
        ArrayList old = new ArrayList();
        old.Add(1);
        List<int> typed = new List<int>();
        typed.Add(2);

        foreach (var x in old) Show(x);     // x : object
        foreach (int x in old) Show(x);     // cast inserted
        foreach (var x in typed) Show(x);   // x : int
    }
}
