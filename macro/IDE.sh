termide space hsplit --nid side1
termide space vsplit --nid bottom
termide space hsplit --nid editor
termide space vsplit --nid tree
termide space vsplit --sid side1 --nid side2

termide space wa --sid ROOT --size 200 
termide space ha --sid ROOT --size 180 
termide space wa --sid side1 --size 700 
termide space ha --sid bottom --size 150 

termide keybinding set Alt+comma termide space terminal_prev
termide keybinding set Alt+period termide space terminal_next

#dirty fix
termide space feed --sid ROOT --cmd 'termide space ha --sid ROOT --size 180' '<Enter>' 'termide tabs2 editor' '<Enter>'
termide space feed --sid tree --cmd 'termide tree2 editor micro --backup false --rmtrailingws true --tabmovement true --tabstospaces true --eofnewline true --tabmovement true --softwrap true' '<Enter>'

