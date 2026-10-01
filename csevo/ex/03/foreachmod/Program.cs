// 슬라이드 p3-v2-foreach-modify — ForEach 안에서 바꾸면, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<int> xs = new List<int>(new int[] { 1, 2, 3 });
        try
        {
            xs.ForEach(delegate(int x)
            {
                Console.WriteLine("visit " + x);
                if (x == 1) xs.Add(10);         // changes the list
            });
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.Message);
        }
        Console.WriteLine("count " + xs.Count);
    }
}
