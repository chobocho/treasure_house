// 슬라이드 p2-v1-collections — 제네릭 없는 컬렉션, C# 1.0
using System;
using System.Collections;

class App
{
    static void Main()
    {
        Hashtable ages = new Hashtable();
        ages["kim"] = 30;                      // boxed int
        int kim = (int)ages["kim"];            // cast to get it back
        Console.WriteLine("kim: " + kim);
        Console.WriteLine("lee: " + (ages["lee"] == null));

        ArrayList nums = new ArrayList();
        nums.Add(1);
        nums.Add(2);
        nums.Add("3");                         // compiles: it is object
        int sum = 0;
        for (int i = 0; i < nums.Count; i++)
        {
            sum += (int)nums[i];               // fails at the third
            Console.WriteLine("sum = " + sum);
        }
    }
}
