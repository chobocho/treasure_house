// 슬라이드 p2-v1-boxeq — ArrayList 속 정수의 == 함정, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        ArrayList list = new ArrayList();
        list.Add(5);
        list.Add(5);
        Console.WriteLine(list[0] == list[1]);           // references
        Console.WriteLine(list[0].Equals(list[1]));      // values
        Console.WriteLine((int)list[0] == (int)list[1]); // values
        Console.WriteLine(list[0] == list[0]);           // same box
        Console.WriteLine(list.Contains(5));             // Equals
        Console.WriteLine(list.IndexOf(5));
    }
}
