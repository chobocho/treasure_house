// 슬라이드 p12-v11-fl-meta — file 형식의 메타데이터 이름, C# 11
using System;
using System.Linq;

file class MyFileLocalAttribute : Attribute { }   // the proposal's

file class Helper { }

[MyFileLocalAttribute]
public class C
{
    public static void Main()
    {
        var attribute = typeof(C).CustomAttributes.Where(attr =>
            attr.AttributeType == typeof(MyFileLocalAttribute)).First();
        Console.WriteLine(attribute);
        Type h = typeof(Helper);
        Console.WriteLine("Name     : " + h.Name);
        Console.WriteLine("FullName : " + h.FullName);
        Console.WriteLine("IsPublic : " + h.IsPublic);
        Type found = typeof(C).Assembly.GetType("Helper");
        Console.WriteLine("GetType(\"Helper\") : "
            + (found == null ? "null" : found.Name));
    }
}
