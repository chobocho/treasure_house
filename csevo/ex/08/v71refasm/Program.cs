// 슬라이드 p8-v7_1-refasm — -refout 으로 나온 dll 을 읽는다, C# 7.1
using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;

class App
{
    static void Dump(string path)
    {
        using (var pe = new PEReader(File.OpenRead(path)))
        {
            MetadataReader md = pe.GetMetadataReader();
            Console.WriteLine(path + " [ReferenceAssembly]=" +
                Meta.AssemblyAttributes(md)
                    .Contains("ReferenceAssemblyAttribute"));
            foreach (var th in md.TypeDefinitions)
            {
                TypeDefinition t = md.GetTypeDefinition(th);
                string type = md.GetString(t.Name);
                if (type != "Lib" && type != "Pair") continue;
                foreach (var fh in t.GetFields())
                    Console.WriteLine("  field  {0}.{1}", type,
                        md.GetString(md.GetFieldDefinition(fh).Name));
                foreach (var mh in t.GetMethods())
                {
                    MethodDefinition m = md.GetMethodDefinition(mh);
                    var il = pe.GetMethodBody(m.RelativeVirtualAddress);
                    Console.WriteLine("  method {0}.{1} IL={2}", type,
                        md.GetString(m.Name),
                        BitConverter.ToString(il.GetILBytes()));
                }
            }
        }
    }

    static void Main()
    {
        Dump("bin/a.dll");
        if (File.Exists("bin/ref.dll")) Dump("bin/ref.dll");
    }
}
