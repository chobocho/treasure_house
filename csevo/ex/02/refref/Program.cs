// 슬라이드 p2-v1-refref — 참조 형식을 ref 로 넘기면, C# 1.0
using System;
using System.Collections;

class App
{
    static void Replace(ArrayList list)
    {
        list.Add("added");            // the caller sees this
        list = new ArrayList();       // only the local copy changes
        list.Add("lost");
    }

    static void ReplaceRef(ref ArrayList list)
    {
        list = new ArrayList();       // the caller's variable changes
        list.Add("new list");
    }

    static void Main()
    {
        ArrayList a = new ArrayList();
        Replace(a);
        Console.WriteLine(a.Count + " " + a[0]);
        ReplaceRef(ref a);
        Console.WriteLine(a.Count + " " + a[0]);
    }
}
